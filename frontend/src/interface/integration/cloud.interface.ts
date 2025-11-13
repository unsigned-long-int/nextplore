export const Cloud = {
    AWS: 'aws',
    AZURE: 'azure',
    GCP: 'gcp',
    SNOWFLAKE_MANAGED: 'snowflake_managed',
} as const;
export type Cloud = typeof Cloud[keyof typeof Cloud];