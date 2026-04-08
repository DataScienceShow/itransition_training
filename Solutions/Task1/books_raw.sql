

USE Itransition

IF OBJECT_ID('tasks.books_raw', 'U') IS NOT NULL
    DROP TABLE tasks.books_raw;

CREATE TABLE tasks.books_raw (
    id          NVARCHAR(50) NOT NULL,
    title       NVARCHAR(500),
    author      NVARCHAR(255),
    genre       NVARCHAR(100),
    publisher   NVARCHAR(255),
    year        INT,
    price       NVARCHAR(20),

    CONSTRAINT PK_books_raw PRIMARY KEY (id)
);


select * from tasks.books_raw

-- drop table tasks.books_raw