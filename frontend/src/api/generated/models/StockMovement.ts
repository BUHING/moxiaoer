/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MovementTypeEnum } from './MovementTypeEnum';
export type StockMovement = {
    readonly id: string;
    product_id: string;
    product_name: string;
    unit_name: string;
    movement_type: MovementTypeEnum;
    quantity_delta: string;
    source_type: string;
    source_id: string;
    readonly occurred_at: string;
    readonly operator_name: string;
    remark?: string;
};

