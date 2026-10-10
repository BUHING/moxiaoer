/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CurrentUser = {
    readonly id: string;
    /**
     * 必填；长度为150个字符或以下；只能包含字母、数字、特殊字符“@”、“.”、“-”和“_”。
     */
    username: string;
    display_name?: string;
    readonly organization_id: string;
    readonly organization_name: string;
    readonly role: string;
    readonly permissions: Array<string>;
};

