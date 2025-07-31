export interface ModelInfo {
    model_id: string;
    label: string;
    tags: string[];
  }
  
export interface AvailableModelsResponse {
    models: ModelInfo[];
}