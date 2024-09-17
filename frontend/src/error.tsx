import { useRouteError } from 'react-router-dom';

export default function Error() {
    const error: unknown = useRouteError();
    console.error(error);

    return (
        <div>
            <h1>Error</h1>
            <p>{(error as Error)?.message || (error as { statusText?: string })?.statusText}</p>
        </div>
    );
}