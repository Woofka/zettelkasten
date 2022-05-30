#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE zettelkasten;
  CREATE USER app with encrypted password '0000';
  GRANT ALL PRIVILEGES ON DATABASE zettelkasten TO app;
EOSQL

psql -v ON_ERROR_STOP=1 --username "app" --dbname "zettelkasten" <<-EOSQL
  CREATE EXTENSION pgcrypto;

  create table users (
    id serial primary key,
    email varchar (320) not null unique,
    password_hash text not null,
    dt_added timestamp
  );

  create table notes (
    id serial primary key,
    user_id int
        references users(id)
        on delete cascade,
    local_id int not null,
    title varchar (200),
    text varchar (3000),
    dt_added timestamp not null,
    dt_edited timestamp,
    constraint note_constrain unique (user_id, local_id)
  );

  create table user_tags (
    id serial primary key,
    user_id int not null
        references users(id)
        on delete cascade,
    tag varchar (50) not null,
    constraint tag_constrain unique (user_id, tag)
  );

  create table note_tags (
    id serial primary key,
    tag_id int not null
        references user_tags(id)
        on delete cascade,
    note_id int not null
        references notes(id)
        on delete cascade
  );
EOSQL
