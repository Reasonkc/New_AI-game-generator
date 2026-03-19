import { useState } from "react";
import { ChevronDown, ChevronUp, Clock, Zap } from "lucide-react";
import { gameTemplates } from "../data/gameTemplates";

export default function TemplateSelector({ onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const [selectedId, setSelectedId] = useState(null);

  const handleSelect = (template) => {
    setSelectedId(template.id);
    onSelect({
      title: template.title,
      description: template.description,
    });
  };

  const visibleTemplates = expanded ? gameTemplates : gameTemplates.slice(0, 3);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Or start from a template
        </h3>
        {gameTemplates.length > 3 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
          >
            {expanded ? (
              <>
                Show less <ChevronUp size={16} className="ml-1" />
              </>
            ) : (
              <>
                Show all <ChevronDown size={16} className="ml-1" />
              </>
            )}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {visibleTemplates.map((template) => (
          <button
            key={template.id}
            onClick={() => handleSelect(template)}
            className={`group relative text-left p-4 rounded-xl border-2 transition-all duration-200 hover:shadow-md ${
              selectedId === template.id
                ? `${template.borderColor} ${template.bgLight} shadow-md`
                : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <div className="flex items-start space-x-3">
              <span className="text-2xl">{template.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900 text-sm">
                  {template.name}
                </div>
                <div className="text-xs text-gray-500 mt-1 truncate">
                  {template.title}
                </div>
                <div className="flex items-center space-x-3 mt-2">
                  <span className="flex items-center text-xs text-gray-400">
                    <Clock size={10} className="mr-1" />
                    {template.playTime}
                  </span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                      template.difficulty === "Easy"
                        ? "bg-green-100 text-green-700"
                        : template.difficulty === "Medium"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {template.difficulty}
                  </span>
                </div>
              </div>
            </div>

            {selectedId === template.id && (
              <div
                className={`absolute top-2 right-2 w-5 h-5 rounded-full bg-gradient-to-r ${template.color} flex items-center justify-center`}
              >
                <Zap size={12} className="text-white" />
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
