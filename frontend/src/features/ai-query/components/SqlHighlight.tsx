
const KEYWORDS = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET|AS|AND|OR|NOT|IN|IS|NULL|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|INSERT|INTO|VALUES|UPDATE|SET|DELETE|WITH|UNION|ALL|EXISTS|BY)\b/gi;

export const SqlHighlight = ({ sql }: { sql: string }) => {
    const parts = sql.split(KEYWORDS);
    return (
        <>
            {parts.map((part, i) =>
                KEYWORDS.test(part) ? (
                    <span key={i} style={{ color: '#c084fc', fontWeight: 600 }}>
                        {part}
                    </span>
                ) : (
                    <span key={i}>{part}</span>
                )
            )}
        </>
    );
};