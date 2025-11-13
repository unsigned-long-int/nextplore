import { Auth } from './auth.interface';
import { DB } from './db.interface';
import { Cloud } from './cloud.interface';

export interface IntegrationProfile {
    id: string;
    auth: Auth;
    cloud: Cloud;
    db: DB;
    connection_name: string;
    host: string;
    database_name: string;
    port?: number | null;
    autosync_on: boolean;
};

