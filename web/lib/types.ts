export interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
}

export interface ExtractResponse {
  entities: Entity[];
}

export interface KGResponse {
  cypher: string;
  rows: Record<string, unknown>[];
  count: number;
}

export interface Citation {
  chunk_id: number;
  score: number;
}

export interface RAGResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
}