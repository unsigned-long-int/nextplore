import { Center, Text } from '@mantine/core';
import '@/styles/LoadingOverlay.css'

interface LoadingOverlayProps {
  loadingText: string;
}


export const LoadingOverlay = ({ loadingText }: LoadingOverlayProps) => {
    return (
        <div className="loader-overlay">
            <Center className="loader-content">
                <div className="snail-loader">
                    <div className="shell" />
                    <div className="body">
                        <div className="eye eye-left" />
                        <div className="eye eye-right" />
                    </div>
                </div>
                <Text className="loading-text">{loadingText}</Text>
            </Center>
        </div>
    );
};