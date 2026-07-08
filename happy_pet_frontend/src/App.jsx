import React from 'react';
// Import your new grid component from the components folder
import ProductGrid from './components/ProductGrid';

function App() {
  return (
    <div className="min-h-screen bg-stone-50">
      {/* 
        This is where your top navigation bar would eventually go 
      */}
      
      {/* Render the ProductGrid here */}
      <ProductGrid />
      
      {/* 
        This is where your footer would eventually go 
      */}
    </div>
  );
}

export default App;