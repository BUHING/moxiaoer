/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PermissionRequestStatusEnum } from './PermissionRequestStatusEnum';
export type PermissionRequest = {
    readonly id: string;
    readonly employee_id: string;
    readonly employee_name: string;
    permission_code: string;
    status?: PermissionRequestStatusEnum;
    reviewed_at?: string | null;
    readonly created_at: string;
};

