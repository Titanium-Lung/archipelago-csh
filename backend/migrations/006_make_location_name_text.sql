alter table public.locations
    alter column location_name type text using location_name::text;