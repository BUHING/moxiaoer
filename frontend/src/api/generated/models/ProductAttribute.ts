/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AttributeOption } from './AttributeOption';
import type { InputTypeEnum } from './InputTypeEnum';
export type ProductAttribute = {
    readonly id: string;
    name: string;
    input_type: InputTypeEnum;
    is_active?: boolean;
    readonly options: Array<AttributeOption>;
    readonly created_at: string;
    readonly updated_at: string;
};

