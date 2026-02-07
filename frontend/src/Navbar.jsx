import { useState } from 'react';
import { User, LogOut, Sparkles, Gamepad2, Code, Menu, X } from 'lucide-react';
import { getRandomName } from './getRandomName';

const Navbar = () => {
    const [showUserInfo, setShowUserInfo] = useState(false);
    const [showMobileMenu, setShowMobileMenu] = useState(false);
    const [userName] = useState(getRandomName());
    const [isLoggedIn, setIsLoggedIn] = useState(true); // Simple state for demo
    
    const toggleUserInfo = () => {
        setShowUserInfo(!showUserInfo);
    };
    
    const handleLogout = () => {
        setIsLoggedIn(false);
        setShowUserInfo(false);
    };
    
    const handleLogin = () => {
        setIsLoggedIn(true);
    };

      

  return (
    <header className="bg-white shadow-lg border-b border-gray-100 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <button 
            onClick={() => window.location.href = "/"}
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
          >
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-2">
              <Sparkles size={24} className="text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                AI Game Generator
              </h1>
            </div>
          </button>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <a 
              href="/"
              className="flex items-center space-x-2 text-gray-700 hover:text-indigo-600 transition-colors font-medium"
            >
              <Gamepad2 size={18} />
              <span>Browse Games</span>
            </a>
            
            <a 
              href="/create"
              className="flex items-center space-x-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-2 rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Code size={18} />
              <span>Create Game</span>
            </a>
          </nav>

          {/* Desktop User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            {isLoggedIn ? (
              <div className="relative">
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">{userName}</div>
                    <div className="text-xs text-gray-500">Game Creator</div>
                  </div>
                  <button 
                    onClick={toggleUserInfo}
                    className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 shadow-lg"
                  >
                    <User size={18} className="text-white" />
                  </button>
                </div>
                
                {showUserInfo && (
                  <div className="absolute right-0 mt-3 w-72 bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 z-20">
                    <div className="flex items-center space-x-4 mb-6">
                      <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                        <User size={20} className="text-white" />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900">{userName}</h3>
                        <p className="text-sm text-gray-500">AI Game Creator</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="bg-green-50 rounded-xl p-3 text-center">
                        <div className="text-lg font-bold text-green-600">5</div>
                        <div className="text-xs text-green-700">Games Created</div>
                      </div>
                      <div className="bg-blue-50 rounded-xl p-3 text-center">
                        <div className="text-lg font-bold text-blue-600">Active</div>
                        <div className="text-xs text-blue-700">Status</div>
                      </div>
                    </div>
                    
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors duration-200 flex items-center justify-center font-medium"
                    >
                      <LogOut size={16} className="mr-2" /> 
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={handleLogin}
                className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 font-medium shadow-lg"
              >
                Sign In
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="md:hidden p-2 text-gray-700 hover:text-indigo-600 transition-colors"
          >
            {showMobileMenu ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {showMobileMenu && (
          <div className="md:hidden border-t border-gray-100 py-4">
            <nav className="space-y-4">
              <a 
                href="/"
                className="flex items-center space-x-3 text-gray-700 hover:text-indigo-600 transition-colors font-medium py-2"
                onClick={() => setShowMobileMenu(false)}
              >
                <Gamepad2 size={18} />
                <span>Browse Games</span>
              </a>
              
              <a 
                href="/create"
                className="flex items-center space-x-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-3 rounded-xl font-medium"
                onClick={() => setShowMobileMenu(false)}
              >
                <Code size={18} />
                <span>Create Game</span>
              </a>
              
              {isLoggedIn ? (
                <div className="border-t border-gray-100 pt-4 mt-4">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                      <User size={18} className="text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{userName}</div>
                      <div className="text-sm text-gray-500">Game Creator</div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => {
                      handleLogout();
                      setShowMobileMenu(false);
                    }}
                    className="w-full px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors flex items-center justify-center font-medium"
                  >
                    <LogOut size={16} className="mr-2" /> 
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="border-t border-gray-100 pt-4 mt-4">
                  <button
                    onClick={() => {
                      handleLogin();
                      setShowMobileMenu(false);
                    }}
                    className="w-full px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 font-medium"
                  >
                    Sign In
                  </button>
                </div>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  )
}

export default Navbar
