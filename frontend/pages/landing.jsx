import { useRouter } from 'next/router';

export default function LandingPage() {
  const router = useRouter();

  // Simulación de inicio de sesión. En una app real, esto
  // estaría conectado a un proveedor de autenticación.
  const handleLogin = () => {
    router.push('./tools/dashboard');
  };

  return (
    <div className="min-h-screen bg-background font-sans text-text-main flex flex-col">
      {/* Header simple para la landing */}
      <header className="py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <h1 className="text-2xl font-extrabold">
            Stream<span className="text-primary">Sculptor</span>
          </h1>
          <button
            onClick={handleLogin}
            className="px-5 py-2 bg-secondary text-text-main font-semibold rounded-lg hover:bg-primary/50 transition-colors"
          >
            Sign In
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow flex items-center">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-5xl md:text-7xl font-extrabold max-w-4xl mx-auto leading-tight">
            Turn Your Long Videos Into <span className="text-primary">Viral-Ready</span> Clips
          </h2>
          <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto mt-6">
            Our AI finds the most engaging moments in your content, so you don't have to.
            Generate clips, transcribe audio, and create subtitles in minutes.
          </p>
          <button
            onClick={handleLogin}
            className="mt-10 px-10 py-4 bg-primary text-white font-bold rounded-lg text-lg hover:bg-primary-hover transition-transform transform hover:scale-105"
          >
            Get Started for Free
          </button>
        </div>
      </main>
      
      {/* Footer simple */}
      <footer className="py-6 text-center text-text-secondary text-sm">
        <p>&copy; 2025 StreamSculptor. All Rights Reserved.</p>
      </footer>
    </div>
  );
}
