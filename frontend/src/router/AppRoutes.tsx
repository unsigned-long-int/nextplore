import { Route, Routes } from 'react-router-dom';

import { RegisterPage } from '@/features/onboarding/pages/RegisterPage';
import { CheckEmailPage } from '@/features/onboarding/pages/CheckEmailPage';
import { VerifyEmailPage } from '@/features/onboarding/pages/VerifyEmailPage';
import { PendingPage } from '@/features/onboarding/pages/PendingPage';
import { RejectedPage } from '@/features/onboarding/pages/RejectedPage';
import { SuspendedPage } from "@/features/onboarding/pages/SuspendedPage";
import { AiQueryPage } from '@/features/ai-query/pages/AiQueryPage';
import { DatastorePage } from '@/features/integration/pages/DatastorePage.tsx';
import { UserProfilePage } from '@/features/user/pages/UserProfilePage';
import { MetaPage } from '@/features/meta/pages/MetaPage';
import { NavigationPage } from '@/features/navigation/pages/NavigationPage';
import { LlmPage } from '@/features/integration/pages/LlmPage';
import {AdminConsentPage} from "@/features/onboarding/pages/AdminConsentPage.tsx";
import {AuthCallback} from "@/features/login/pages/AuthCallback.tsx";


export const AppRoutes = () => (
    <Routes>
        <Route path='/register' element={<RegisterPage />} />
        <Route path='/register/check-email' element={<CheckEmailPage />} />
        <Route path='/register/verify' element={<VerifyEmailPage />} />
        <Route path='/register/pending' element={<PendingPage />} />
        <Route path='/register/rejected' element={<RejectedPage />} />
        <Route path='/suspended' element={<SuspendedPage />} />
        <Route path='/admin-consent' element={<AdminConsentPage />} />
        <Route path='/auth-callback' element={<AuthCallback />} />

        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<AiQueryPage />} />
            <Route path='llm' element={<LlmPage />} />
            <Route path='datastores' element={<DatastorePage/>} />
            <Route path='metadata' element={<MetaPage/>} />
        </Route>
    </Routes>
); 