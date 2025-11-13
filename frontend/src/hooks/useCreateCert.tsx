import axios from "axios";
import type { CertCreateRequest } from '../interface/integration/cert-create-request.interface';
import { useTokenProvider } from "../authentication/useTokenProvider";

export const useCreateCert = () => {
  const { getToken } = useTokenProvider();

  const createCert = async (data: CertCreateRequest): Promise<void> => {
    const token = await getToken();
    await axios.post(
      "http://localhost:8005/v1/nextplore-orchestrator/integrations/certificates",
      data,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );
  };

  return { createCert };
};

