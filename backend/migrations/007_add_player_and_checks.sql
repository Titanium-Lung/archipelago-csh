alter table public.slots
    add player_uuid varchar(50) default null;

alter table public.slots
    add checks integer default 0;