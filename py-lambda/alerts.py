import os
import json
from enum import StrEnum
from dataclasses import dataclass, field

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
    Get mental health alerts.

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
        'mental_health_score' and 'timestamp'. 
    """
    query = sql.SQL(
        "SELECT record_id, score, timestamp "
        "FROM high_stress_alerts "
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
                "mental_health_score": row[1],
                "timestamp": row[2].isoformat(),
            }
            for row in cur.fetchall()
        ]
    

@dataclass
class AlertsEvent:
    limit: int = field(default=10)
    offset: int = field(default=0)
    order_by: OrderBy = field(default=OrderBy.TIMESTAMP)
    direction: SortDirection = field(default=SortDirection.DESC)

    def __post_init__(self):
        validation_errors = []
        if not isinstance(self.limit, int):
            validation_errors.append(f"received type '{type(self.limit)}' for 'limit' field; expected 'int'")
        if not isinstance(self.offset, int):
            validation_errors.append(f"received type '{type(self.offset)}' for 'offset' field; expected 'int'")
        if not isinstance(self.order_by, (str, OrderBy)) or self.order_by not in OrderBy:
            validation_errors.append(f"received '{self.order_by}' for 'order_by' field; expected either 'timestamp' or 'score'")
        if not isinstance(self.direction, (str, SortDirection)) or self.direction not in SortDirection:
            validation_errors.append(f"received '{self.direction}' for 'direction' field; expected either 'DESC' or 'ASC'")
        if validation_errors:
            raise ValueError(f"alerts event validation failed with: {validation_errors}")


def lambda_handler(event, context):
    try:
        # unpack event
        params = AlertsEvent(**json.loads(event.get("body", "{}")))

        with psycopg2.connect(
            host=os.environ["DB_HOST"],
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            port=os.environ.get("DB_PORT", "5432"),
        ) as conn:

            # get records above threshold
            records = get_alerts(
                conn,
                limit=params.limit,
                offset=params.offset,
                order_by=params.order_by,
                direction=params.direction,
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
