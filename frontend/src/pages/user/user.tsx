import { useState } from "react";
import { useAddAPIKey, useDeleteAPIKey, useGetAPIKeys, useUser } from "../../hooks";
import Sidebar from "../../ui/sidebar/sidebar";
import styles from './user.module.scss';
import { MODEL_API_PROVIDERS } from "../../types";

export default function User() {

    const {user} = useUser();

    const {data, isLoading} = useGetAPIKeys();

    const addKeyMutation = useAddAPIKey();
    const deleteKeyMutation = useDeleteAPIKey();

    const [updateUser, setUpdateUser] = useState({...user, password: '', confirmPassword: ''});

    const [updateAPIKeys, setUpdateAPIKeys] = useState<Record<string, string>>(Object.fromEntries(MODEL_API_PROVIDERS.map(p => [p, ''])));

    const handleAPIKeySave = (provider: string) => {
        if (!updateAPIKeys[provider]) {
            return;
        }
        addKeyMutation.mutate({provider, key: updateAPIKeys[provider]});
        setUpdateAPIKeys(val => ({...val, [provider]: ''}));
    }

    const renderAPIInput = (provider: string, index: number) => {
        const key = data!.find(k => k.provider === provider);
        
        return <div className={styles.formItem + ' ' + styles.apiKeyItem} key={index}>
            <label htmlFor="key">{provider}</label>
            <input type='password' id="key" value={updateAPIKeys[provider]} placeholder={key ? '.......' : ''} onChange={(e) => setUpdateAPIKeys({...updateAPIKeys, [provider]: e.target.value})} />
            {updateAPIKeys[provider] && <button onClick={() => handleAPIKeySave(provider)}>Save</button>}
            {key && <button onClick={() => deleteKeyMutation.mutate(provider)}>Delete</button>}
        </div>
    }
    
    return (
        <div className={styles.userPage}>
            <Sidebar />
            <div className={styles.content}>
                <h1>Edit User</h1>
                <form className={styles.form}>
                    <div className={styles.formItem}>
                        <label htmlFor="email">Email</label>
                        <input type="email" id="email" value={updateUser.email} onChange={(e) => setUpdateUser({...updateUser, email: e.target.value})} />
                    </div>
                    <div className={styles.formItem}>
                        <label htmlFor="password">Password</label>
                        <input type="password" id="password" value={updateUser.password} onChange={(e) => setUpdateUser({...updateUser, password: e.target.value})} />
                    </div>
                    <div className={styles.formItem}>
                        <label htmlFor="confirmPassword">Confirm Password</label>
                        <input type="password" id="confirmPassword" value={updateUser.confirmPassword} onChange={(e) => setUpdateUser({...updateUser, confirmPassword: e.target.value})} />
                        {updateUser.confirmPassword !== '' && updateUser.password !== updateUser.confirmPassword && <p className={styles.error}>Passwords do not match</p>}
                    </div>
                    <button type="submit">Save</button>
                </form>
                {!isLoading && data && <>
                    <h1>API Keys</h1>
                    {MODEL_API_PROVIDERS.map(renderAPIInput)}
                </>}
            </div>
        </div>
    )
}