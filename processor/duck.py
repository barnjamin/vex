import duckdb

path = "/tmp/blocks/*.json"

def import_blocks():
    con = duckdb.connect("vex.db")
    create_txn = """
    DROP TABLE IF EXISTS blocks;
    CREATE TABLE blocks (
        round UBIGINT,
        ts UBIGINT,
        prev VARCHAR
    );
    """
    con.execute(create_txn)

    blocks_insert = """
        DELETE FROM blocks WHERE true;
        INSERT INTO blocks 
            SELECT 
                block->>'$.rnd' as round, 
                block->>'$.ts' as ts, 
                block->>'$.prev' as prev, 
            FROM read_json('"""+path+"""', columns={block: JSON})
    """
    con.execute(blocks_insert)
    con.close()

def import_boxes():
    con = duckdb.connect("vex.db")
    create_boxes_table = """
    DROP TABLE IF EXISTS boxes;
    CREATE TABLE boxes (
        round UBIGINT,
        app_id BLOB,
        name BLOB,
        data BLOB 
    );
    """
    con.execute(create_boxes_table)

    boxes_insert = """
    INSERT INTO boxes
        SELECT 
            round,
            key[4:11]::BLOB as app_id,
            key[12:]::BLOB as name,
            from_base64(boxes->key->>'Data') as data
        FROM (
            SELECT 
                block->'$.rnd' as round,
                delta->'$.KvMods' as boxes,
                UNNEST(json_keys(delta, '$.KvMods')) as key
            FROM read_json('"""+path+"""', columns={block: JSON, delta: JSON})
        );
    """
    con.execute(boxes_insert)

    con.close()


def import_txns():
    con = duckdb.connect("vex.db")

    create_txn = """
    DROP TABLE IF EXISTS txns;
    CREATE TABLE txns (
        round UINTEGER,
        delta JSON,
        txn JSON
    );
    """
    con.execute(create_txn)

    txn_insert = """
        DELETE FROM txns WHERE true;
        INSERT INTO txns SELECT 
            round, 
            payset->payset_idx->'$.dt' as delta, 
            payset->payset_idx->'$.txn' as txn,
        FROM (
            SELECT 
                block->>'$.rnd' as round, 
                block->>'$.ts' as ts, 
                payset,
                unnest(range(0, json_array_length(payset)::BIGINT)) as payset_idx
            FROM read_json('"""+path+"""', columns={block: JSON, payset: JSON})
        );
    """
    con.execute(txn_insert)
    con.close()




import_blocks()
import_txns()
import_boxes()


db = duckdb.connect("vex.db")
db.sql("SELECT txns.round, blocks.ts, txns.txn->>'snd' FROM txns JOIN blocks ON blocks.round=txns.round").show()