export type WorkflowState='NEW_REVIEW'|'REVIEWING'|'FIRST_REVIEW_COMPLETE'|'WAITING_FOR_FIRST_DECISIONS'|'GENERATING_OPTIMIZED_DRAFT'|'OPTIMIZED_DRAFT_READY'|'SECOND_REVIEWING'|'SECOND_REVIEW_COMPLETE'|'WAITING_FOR_SECOND_DECISIONS'|'GENERATING_FINAL'|'READY_TO_DELIVER'|'FAILED'
export type Decision='accepted'|'ignored'|'regenerate'
export interface Issue {id:string;priorityLabel:string;categoryLabel:string;title:string;description:string;originalText:string;suggestedText:string;ruleReference:string;decision:Decision|null;isMandatory:boolean}
export interface Summary {autoFixedCount:number;pendingCount:number;acceptedCount:number;ignoredCount:number;complianceStatus:string}
export interface Draft {titles:string[];content:string;tags:string[];changes:string[];validation:Record<string,unknown>}
export interface Session {id:string;state:WorkflowState;createdAt:string;updatedAt:string;sourceFilename:string;taskSummary:string;reviewFocus:string[];reviewBasis:{key:string;label:string;version:string;count:number}[];summary:Summary;firstReview:Issue[];optimizedDraft:Draft|null;secondReview:Issue[];finalVersion:Draft|null;error:string|null}
