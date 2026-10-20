import argparse
import os
from getpass import getpass
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from neo4j import GraphDatabase

# python .\import_retailrockect.py -p ....

# 1. Mengatur argumen program
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Impor dataset RetailRocket ke Neo4j"
    )

    parser.add_argument(
        "-u", "--user",
        default="neo4j",
        help="Username Neo4j"
    )
    
    # Menambahkan argumen password
    parser.add_argument(
        "-p", "--password",
        required=True,
        help="Password Neo4j"
    )

    parser.add_argument(
        "-b", "--bolt",
        default="neo4j://localhost:7687",
        help="Alamat koneksi Neo4j"
    )

    parser.add_argument(
        "-s", "--source",
        default="data/processed/events_filtered.csv",
        help="Lokasi file CSV"
    )

    parser.add_argument(
        "--database",
        default="utsretailrocket",
        help="Nama database tujuan"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Jumlah baris dalam satu batch"
    )

    return parser.parse_args()


# 2. Membuat constraint untuk node
def create_constraints(session):
    session.run("""
        CREATE CONSTRAINT visitor_id_unique IF NOT EXISTS
        FOR (v:Visitor)
        REQUIRE v.visitorId IS UNIQUE
    """).consume()

    session.run("""
        CREATE CONSTRAINT item_id_unique IF NOT EXISTS
        FOR (i:Item)
        REQUIRE i.itemId IS UNIQUE
    """).consume()

    print("Constraint Visitor dan Item berhasil dibuat.")


# 3. Fungsi impor satu batch
def import_batch(tx, batch):
    cypher_query = """
    UNWIND $batch AS row

    MERGE (v:Visitor {visitorId: row.visitorid})
    MERGE (i:Item {itemId: row.itemid})

    WITH v, i, row

    CALL (v, i, row) {
        WITH v, i, row
        WHERE row.event = 'view'

        CREATE (v)-[:VIEWED {
            timestamp: row.timestamp,
            periode: row.periode
        }]->(i)

        UNION ALL

        WITH v, i, row
        WHERE row.event = 'addtocart'

        CREATE (v)-[:ADDED_TO_CART {
            timestamp: row.timestamp,
            periode: row.periode
        }]->(i)

        UNION ALL

        WITH v, i, row
        WHERE row.event = 'transaction'

        CREATE (v)-[:BOUGHT {
            timestamp: row.timestamp,
            transactionId: row.transactionid,
            periode: row.periode
        }]->(i)
    }
    """

    tx.run(cypher_query, batch=batch).consume()


# 4. Program utama
def main():
    args = parse_arguments()

    csv_file_path = Path(args.source)

    # Memeriksa keberadaan file
    if not csv_file_path.is_file():
        print(f"File tidak ditemukan: {csv_file_path}")
        return

    if args.batch_size <= 0:
        print("Batch size harus lebih dari 0.")
        return

    print("File ditemukan:", csv_file_path)

    # password = os.getenv("NEO4J_PASSWORD")

    # if not password:
    #     password = getpass("Masukkan password Neo4j: ")
    # Menggunakan password dari argument CLI
    password = args.password
    # Membuat koneksi
    with GraphDatabase.driver(
        args.bolt,
        auth=(args.user, password)
    ) as driver:

        driver.verify_connectivity()
        print("Koneksi Neo4j berhasil.")

        with driver.session(database=args.database) as session:

            # Menghindari impor ulang ke database berisi data
            existing_nodes = session.run(
                "MATCH (n) RETURN count(n) AS total"
            ).single()["total"]

            if existing_nodes != 0:
                print(
                    "Impor dibatalkan: database belum kosong. "
                    "Periksa data yang sudah ada terlebih dahulu."
                )
                return

            create_constraints(session)

            print("Membaca data:", csv_file_path)

            chunks = pd.read_csv(
                csv_file_path,
                chunksize=args.batch_size,
                dtype={"transactionid": "string"}
            )

            total_imported = 0

            print("Memulai proses impor...")

            for chunk in tqdm(
                chunks,
                desc="Mengimpor Batch Data"
            ):
                required = {
                    "timestamp", "visitorid", "event",
                    "itemid", "transactionid", "periode"
                }

                if not required.issubset(chunk.columns):
                    raise ValueError(
                        "Kolom CSV tidak lengkap."
                    )

                if chunk[list(required - {"transactionid"})].isna().any().any():
                    raise ValueError("Ada nilai wajib yang kosong.")

                if not chunk["event"].isin(
                    ["view", "addtocart", "transaction"]
                ).all():
                    raise ValueError("Ditemukan jenis event tidak valid.")

                if not chunk["periode"].isin(["P1", "P2"]).all():
                    raise ValueError("Ditemukan periode tidak valid.")

                chunk["transactionid"] = (
                    chunk["transactionid"]
                    .fillna("")
                    .astype(str)
                )

                chunk["timestamp"] = chunk["timestamp"].astype("int64")
                chunk["visitorid"] = chunk["visitorid"].astype("int64")
                chunk["itemid"] = chunk["itemid"].astype("int64")

                records = chunk.to_dict(orient="records")

                session.execute_write(import_batch, records)

                total_imported += len(records)

            print("\nProses impor berhasil.")
            print("Total interaksi diimpor:", total_imported)


if __name__ == "__main__":
    main()