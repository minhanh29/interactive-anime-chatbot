-- -------------------------------------------------------------
-- TablePlus 5.4.2(506)
--
-- https://tableplus.com/
--
-- Database: mybot
-- Generation Time: 2023-12-24 18:43:50.2980
-- -------------------------------------------------------------


-- This script only contains the table creation statements and does not fully represent the table in the database. It's still missing: indices, triggers. Do not use it as a backup.

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS yourself_id_seq;

-- Table Definition
CREATE TABLE "public"."yourself" (
    "id" int4 NOT NULL DEFAULT nextval('yourself_id_seq'::regclass),
    "attribute" text,
    "value" text,
    "content" text,
    PRIMARY KEY ("id")
);

