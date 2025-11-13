export const DB = {
    MYSQL: 'mysql',
    SQLSERVER: 'sqlserver',
    POSTGRESQL: 'postgresql',
    SNOWFLAKE: 'snowflake',
} as const;
export type DB = typeof DB[keyof typeof DB];