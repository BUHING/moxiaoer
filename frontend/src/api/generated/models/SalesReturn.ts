/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SalesReturnItem } from './SalesReturnItem';
import type { StatusE3aEnum } from './StatusE3aEnum';
export type SalesReturn = {
    readonly id: string;
    readonly document_no: string;
    customer_id: string | null;
    customer_name?: string | null;
    readonly status: StatusE3aEnum;
    readonly occurred_on: string;
    readonly total_amount: string;
    readonly remark: string;
    completed_by_user_id: string | null;
    readonly completed_at: string | null;
    readonly created_at: string;
    readonly updated_at: string;
    sales_order_id: string;
    sales_order_no: string;
    readonly items: Array<SalesReturnItem>;
};

