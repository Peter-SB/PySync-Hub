// ErrorContext.js
import React, { createContext, useState, useContext } from 'react';

export const GlobalErrorContext = createContext();

export const GlobalErrorProvider = ({ children }) => {
    const [error, setError] = useState(null);

    return (
        <GlobalErrorContext.Provider value={{ error, setError }}>
            {children}
        </GlobalErrorContext.Provider>
    );
};

export const useGlobalError = () => {
    const context = useContext(GlobalErrorContext);
    if (!context) throw new Error("useGlobalError must be used within GlobalErrorProvider");
    return context;
};