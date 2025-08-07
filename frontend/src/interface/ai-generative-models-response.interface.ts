export interface ModelInfo {
    provider: string;
    model_id: string;
    label: string;
    tags: string[];
  }
  
export interface AvailableModelsResponse {
    models: ModelInfo[];
}