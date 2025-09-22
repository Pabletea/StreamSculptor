import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

// Iconos SVG simples para el UI
const ToolsIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
);
const UserIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
);
const SunIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="5" strokeWidth="2" />
        <path strokeLinecap="round" strokeWidth="2" d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
);
const MoonIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" />
    </svg>
);

export default function Layout({ children }) {
    const [toolsOpen, setToolsOpen] = useState(false);
    const [profileOpen, setProfileOpen] = useState(false);
    const toolsRef = useRef(null);
    const profileRef = useRef(null);
    const router = useRouter();

    // Hook para cerrar los desplegables si se hace clic fuera de ellos
    useEffect(() => {
        function handleClickOutside(event) {
            if (toolsRef.current && !toolsRef.current.contains(event.target)) {
                setToolsOpen(false);
            }
            if (profileRef.current && !profileRef.current.contains(event.target)) {
                setProfileOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [toolsRef, profileRef]);

    // Simulación de logout
    const handleLogout = () => {
        // Aquí iría la lógica real de logout (limpiar token, etc.)
        console.log("User logged out");
        router.push('/'); // Redirigir a la landing page
    };

    const [isDark, setIsDark] = useState(false);

    useEffect(() => {
        setIsDark(document.documentElement.classList.contains("dark"));
    }, []);

    const toggleTheme = () => {
        const newDark = !isDark;
        setIsDark(newDark);
        document.documentElement.classList.toggle("dark", newDark);
    };

    return (
        <div className="min-h-screen bg-background text-text-main font-sans">
            {/* Barra de Navegación Superior */}
            <header className="bg-surface border-b border-secondary sticky top-0 z-50">
                <div className="container mx-auto px-4">
                    <div className="flex justify-between items-center h-16">
                        {/* Parte Izquierda: Logo y Menú de Herramientas */}
                        <div className="flex items-center gap-8">
                            <Link href="/tools/dashboard" className="text-2xl font-extrabold text-text-main">
                                Stream<span className="text-primary">Sculptor</span>
                            </Link>
                            {/* Menú Desplegable de Herramientas */}
                            <div className="relative" ref={toolsRef}>
                                <button
                                    onClick={() => setToolsOpen(!toolsOpen)}
                                    className="hidden md:flex items-center gap-2 text-text-secondary hover:text-text-main transition-colors"
                                >
                                    <ToolsIcon />
                                    <span>Tools</span>
                                </button>
                                {toolsOpen && (
                                    <div className="absolute mt-2 w-48 bg-surface border border-secondary rounded-lg shadow-lg py-2">
                                        <Link href="/tools/dashboard" className="block px-4 py-2 text-sm text-text-secondary hover:bg-secondary hover:text-text-main">Generate Clips</Link>
                                        <Link href="/tools/transcribe" className="block px-4 py-2 text-sm text-text-secondary hover:bg-secondary hover:text-text-main">Transcribe Video</Link>
                                        <Link href="/tools/subtitle" className="block px-4 py-2 text-sm text-text-secondary hover:bg-secondary hover:text-text-main">Subtitle Video</Link>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Parte Derecha: Perfil de Usuario */}
                        <div className="flex items-center gap-3">
                            {/* Botón de cambio de theme */}
                            <button
                                onClick={toggleTheme}
                                className="flex items-center justify-center w-10 h-10 bg-secondary rounded-full hover:ring-2 hover:ring-primary transition-all"
                                title="Cambiar theme"
                            >
                                {isDark ? <SunIcon /> : <MoonIcon />}
                            </button>
                            {/* Perfil de Usuario */}
                            <div className="relative" ref={profileRef}>
                                <button
                                    onClick={() => setProfileOpen(!profileOpen)}
                                    className="flex items-center justify-center w-10 h-10 bg-secondary rounded-full hover:ring-2 hover:ring-primary transition-all"
                                >
                                    <UserIcon />
                                </button>
                                {profileOpen && (
                                    <div className="absolute right-0 mt-2 w-48 bg-surface border border-secondary rounded-lg shadow-lg py-2">
                                        <div className="px-4 py-2 border-b border-secondary">
                                            <p className="text-sm text-text-main font-semibold">User Name</p>
                                            <p className="text-xs text-text-secondary truncate">user.email@example.com</p>
                                        </div>
                                        <Link href="/profile" className="block px-4 py-2 text-sm text-text-secondary hover:bg-secondary hover:text-text-main">My Account</Link>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-secondary"
                                        >
                                            Log Out
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Contenido de la Página */}
            <main>
                {children}
            </main>
            <footer className="bg-surface border-t border-secondary mt-8 py-4">
                <div className="container mx-auto px-4 text-center text-sm text-text-secondary">
                    © {new Date().getFullYear()} StreamSculptor. Todos los derechos reservados.
                </div>
            </footer>
        </div>

    );
}
