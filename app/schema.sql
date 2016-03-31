drop table if exists plants;
create table plants (
  id integer primary key autoincrement,
  name text not null,
  photo_url text not null,
  water_ideal real not null,
  water_tolerance real not null,
  light_ideal real not null,
  light_tolerance real not null,
  humidity_ideal real not null,
  humidity_tolerance real not null,
  temperature_ideal real not null,
  temperature_tolerance real not null,
  mature_on timestamp not null,
  slot_id integer not null unique,
  plant_database_id integer not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists sensor_data_points;
create table sensor_data_points (
  id integer primary key autoincrement,
  plant_id integer not null,
  sensor_name text not null,
  sensor_value real not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists plant_settings;
create table plant_settings (
  id integer primary key autoincrement,
  plant_id integer not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists notification_thresholds;
create table notification_thresholds (
  id integer primary key autoincrement,
  plant_setting_id integer not null,
  sensor_name text not null,
  deviation_percent integer not null,
  deviation_time real not null,
  triggered_at timestamp default CURRENT_TIMESTAMP,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists tokens;
create table tokens (
  id integer primary key autoincrement,
  token text not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists water_levels;
create table water_levels (
  id integer primary key autoincrement,
  level integer not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists controls;
create table controls (
  id integer primary key autoincrement,
  name text not null,
  enabled boolean not null,
  active boolean,
  disabled_at timestamp,
  active_start timestamp,
  active_end timestamp,
  created_at timestamp not null,
  updated_at timestamp not null
)
