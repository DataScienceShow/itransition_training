USE Itransition

IF OBJECT_ID('tasks.books_summary', 'U') IS NOT NULL
    DROP TABLE tasks.books_summary;

CREATE TABLE tasks.books_summary (
    publication_year INT,
    book_count INT,
    average_price FLOAT
);

INSERT INTO tasks.books_summary (publication_year, book_count, average_price)
SELECT
    year AS publication_year,
    COUNT(*) AS book_count,
    ROUND(
        AVG(
            CASE
                WHEN price LIKE '$%' THEN TRY_CAST(SUBSTRING(price, 2, LEN(price)) AS FLOAT)
                WHEN price LIKE '€%' THEN TRY_CAST(SUBSTRING(price, 2, LEN(price)) AS FLOAT) * 1.2
                ELSE TRY_CAST(price AS FLOAT)
            END
        ), 2
    ) AS average_price
FROM tasks.books_raw
GROUP BY year;


-- drop table tasks.books_summary

select * from tasks.books_summary