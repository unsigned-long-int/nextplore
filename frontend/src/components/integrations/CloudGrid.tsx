type CloudProvider = 'aws' | 'azure' | 'gcp';

const CLOUD_PROVIDERS: { id: CloudProvider; name: string; logoSrc: string }[] = [
    { id: 'aws', name: 'Amazon Web Services', logoSrc: '../../assets/aws-cloud.svg' },
    { id: 'azure', name: 'Microsoft Azure', logoSrc: '../../assets/azure-cloud.svg' },
    { id: 'gcp', name: 'Google Cloud', logoSrc: '../../assets/gcp-cloud.svg' }
];

type CloudProviderPickerProps = {
    value: CloudProvider | null;
    onChange: (v: CloudProvider) => void;
    disabled?: boolean;
};

export const CloudProviderPicker = ({ value, onChange, disabled }: CloudProviderPickerProps) => {

    return (
        <div role="radiogroup" aria-label="Cloud provider" style={{ display: "flex", gap: 12 }}>
            {CLOUD_PROVIDERS.map((cp) => {
            const isSelected = value === cp.id;
            return (
                <button
                key={cp.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                aria-label={cp.name}
                disabled={disabled}
                onClick={() => {
                    if (!isSelected) onChange(cp.id);
                }}
                className={[
                    "rounded-2xl border p-3 bg-white shadow-sm transition",
                    isSelected ? "ring-4 ring-blue-500 border-transparent" : "hover:ring-2 hover:ring-gray-300 border-gray-200",
                ].join(" ")}
                style={{ width: 72, height: 72 }}
                >
                <img src={cp.logoSrc} alt={cp.name} style={{ width: 36, height: 36, objectFit: "contain" }} />
            </button>
          );
        })}
      </div>
    );
  }