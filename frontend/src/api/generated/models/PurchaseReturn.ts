/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PurchaseReturnItem } from './PurchaseReturnItem';
import type { StatusE3aEnum } from './StatusE3aEnum';
export type PurchaseReturn = {
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
    purchase_id: string | null;
    purchase_no?: string | null;
    readonly items: Array<PurchaseReturnItem>;
};

