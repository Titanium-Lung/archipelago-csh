create table released_games
(
    name    varchar(20) not null,
    room_id varchar(50) not null
        constraint released_games_rooms_room_id_fk
            references rooms
            on delete cascade,
    constraint released_games_pk
        primary key (name, room_id)
);