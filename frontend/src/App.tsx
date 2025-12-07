/** Main App component with routing */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './components/layout';
import { ChatPage, SchemaExplorerPage, HistoryPage, SettingsPage } from './pages';

function App() {
    return (
        <BrowserRouter>
            <MainLayout>
                <Routes>
                    <Route path="/" element={<ChatPage />} />
                    <Route path="/schema" element={<SchemaExplorerPage />} />
                    <Route path="/history" element={<HistoryPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                </Routes>
            </MainLayout>
        </BrowserRouter>
    );
}

export default App;
