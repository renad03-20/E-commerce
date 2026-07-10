import React from 'react';
import { useCart } from '../context/CartContext';

const CartSidebar = ({ isOpen, onClose }) => {
  const { cartItems } = useCart();
  
  // Calculate total price
  const cartTotal = cartItems.reduce((total, item) => {
    const price = parseFloat(item.variants?.[0]?.price || 0);
    return total + (price * item.quantity);
  }, 0);

  const handleCheckout = async () => {
    if (cartItems.length === 0) return alert("Cart is empty!");
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/admin/checkout/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: cartItems,
          customer_email: "test@example.com", // We will make this dynamic later
          shipping_address: "123 Pet Lane"
        })
      });
      
      if (response.ok) {
        alert("Order placed successfully! Sending to supplier...");
        localStorage.removeItem('happy-pet-cart');
        window.location.reload(); // Refresh to clear cart
      }
    } catch (error) {
      console.error("Checkout failed", error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-orange-50">
          <h2 className="text-2xl font-bold text-gray-800">Your Cart</h2>
          <button onClick={onClose} className="text-gray-500 font-bold hover:text-orange-500 text-xl">✕</button>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {cartItems.map((item, index) => (
            <div key={index} className="flex justify-between items-center border-b pb-2">
              <div>
                <p className="font-bold text-gray-800 line-clamp-1">{item.title}</p>
                <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
              </div>
              <p className="font-bold text-orange-600">
                ${(parseFloat(item.variants?.[0]?.price || 0) * item.quantity).toFixed(2)}
              </p>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex justify-between font-bold text-xl mb-4 text-gray-800">
            <span>Total:</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>
          <button 
            onClick={handleCheckout}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold py-4 rounded-xl text-lg shadow-lg"
          >
            Checkout Securely
          </button>
        </div>
      </div>
    </div>
  );
};

export default CartSidebar;
