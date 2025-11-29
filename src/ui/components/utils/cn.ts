/**
 * Utility for conditionally joining classNames together.
 * Combines clsx and tailwind-merge functionality.
 * 
 * @example
 * cn('base-class', condition && 'conditional-class', 'override-class')
 */

type ClassValue = string | number | boolean | undefined | null | ClassValue[];

/**
 * Filters and joins class names, removing falsy values
 */
function clsx(...inputs: ClassValue[]): string {
  const classes: string[] = [];

  for (const input of inputs) {
    if (!input) continue;

    if (typeof input === 'string' || typeof input === 'number') {
      classes.push(String(input));
    } else if (Array.isArray(input)) {
      const nested = clsx(...input);
      if (nested) classes.push(nested);
    }
  }

  return classes.join(' ');
}

/**
 * Merge Tailwind CSS classes, resolving conflicts
 * This is a simplified version - in production, use tailwind-merge
 */
function twMerge(classes: string): string {
  // Split into individual classes
  const classList = classes.split(/\s+/).filter(Boolean);
  
  // Group classes by their "type" (prefix before the last dash or the whole class)
  const classMap = new Map<string, string>();
  
  // Patterns to identify conflicting classes
  const conflictPatterns = [
    // Spacing
    /^(p|px|py|pt|pr|pb|pl|m|mx|my|mt|mr|mb|ml)-/,
    // Sizing
    /^(w|h|min-w|min-h|max-w|max-h)-/,
    // Flexbox
    /^(flex|justify|items|content|self)-/,
    // Grid
    /^(grid|col|row|gap)-/,
    // Typography
    /^(text|font|leading|tracking|decoration)-/,
    // Background
    /^(bg|from|via|to)-/,
    // Border
    /^(border|rounded)-/,
    // Effects
    /^(shadow|opacity|blur)-/,
    // Transitions
    /^(transition|duration|ease|delay)-/,
    // Display
    /^(block|inline|hidden|flex|grid|table)/,
    // Position
    /^(static|fixed|absolute|relative|sticky)/,
  ];
  
  for (const cls of classList) {
    let key = cls;
    
    // Find the conflict group
    for (const pattern of conflictPatterns) {
      const match = cls.match(pattern);
      if (match) {
        key = match[0];
        break;
      }
    }
    
    // Later classes override earlier ones with the same key
    classMap.set(key, cls);
  }
  
  return Array.from(classMap.values()).join(' ');
}

/**
 * Combines clsx for conditional classes with tailwind-merge for conflict resolution
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
