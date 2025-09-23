import os
import json
from enum import StrEnum

import psycopg2
from psycopg2 import sql
from psycopg2._psycopg import connection


class SortDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class OrderBy(StrEnum):
    TIMESTAMP = "timestamp"
    SCORE = "score"


def get_alerts(
    conn: connection,
    limit: int,
    offset: int,
    order_by: OrderBy,
    direction: SortDirection,
) -> list[dict[str, int | str]]:
    """
    Get high stress alerts.

    Parameters
    ----------
    conn : connection
        An active database connection.
    limit : int
        Pagination limit.
    offset : int
        Pagination offset.
    order_by : OrderBy
        Column to order alerts by. Takes either 'timestamp' or 'score'.
    direction : SortDirection
        Sorting direction. Takes either 'ASC' or 'DESC'.

    Returns
    -------
    list[dict[str, int | str]]
        A list of dictionaries containing keys 'record_id', 
        'stress_score' and 'timestamp'. 
    """
    query = sql.SQL(
        "SELECT record_id, score, timestamp "
        "FROM high_stress_users "
        "ORDER BY {order_by} {direction} "
        "LIMIT %s "
        "OFFSET %s"
    ).format(
        order_by=sql.SQL(order_by),
        direction=sql.SQL(direction),
    )
    with conn.cursor() as cur:
        cur.execute(
            query, 
            [str(limit), str(offset)]
        )
        return [
            {
                "record_id": row[0],
                "stress_score": row[1],
                "timestamp": row[2].isoformat(),
            }
            for row in cur.fetchall()
        ]


def lambda_handler(event, context):
    try:
        # unpack event
        body = json.loads(event.get("body", "{}"))
        limit = int(body.get("limit", 10))
        offset = int(body.get("offset", 0))
        order_by = OrderBy(body.get("order_by", OrderBy.TIMESTAMP))
        direction = SortDirection(body.get("direction", SortDirection.DESC))

        with psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            database=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
        ) as conn:

            # get records above threshold
            records = get_alerts(
                conn,
                limit=limit,
                offset=offset,
                order_by=order_by,
                direction=direction,
            )
        
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(records),
            }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


if __name__ == "__main__":
    x = lambda_handler(
        event={
            "order_by": "score"
        },
        context={},
    )
    print(x)
