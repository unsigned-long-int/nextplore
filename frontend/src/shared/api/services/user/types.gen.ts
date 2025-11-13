export type UserStats = {
    integrations_number: number;
    vectors_number: number;
};

export type UserProfile = {
    id: string;
    email: string;
    name: string;
    role: string;
    organization: string;
    organization_id: string;
};