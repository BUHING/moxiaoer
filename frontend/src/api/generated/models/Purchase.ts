/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PurchaseItem } from './PurchaseItem';
import type { StatusE3aEnum } from './StatusE3aEnum';
export type Purchase = {
    readonly id: string;
    readonly document_no: string;
    supplier_id: string | null;
    supplier_name?: string | null;
    readonly status: StatusE3aEnum;
    readonly occurred_on: string;
    readonly total_amount: string;
    readonly remark: string;
    completed_by_user_id: string | null;
    readonly completed_at: string | null;
    readonly created_at: string;
    readonly updated_at: string;
    readonly items: Array<PurchaseItem>;
};

