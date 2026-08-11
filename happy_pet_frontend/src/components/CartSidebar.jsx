// src/components/CartSidebar.jsx
import React, { useState } from 'react';
import { useCart } from '../context/CartContext';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';
import CheckoutForm from './CheckoutForm';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const CartSidebar = ({ isOpen, onClose }) => {
  const { cartItems } = useCart();
  const [clientSecret, setClientSecret] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [shippingAddress, setShippingAddress] = useState('');

  const cartTotal = cartItems.reduce((total, item) => {
    const price = parseFloat(item.selectedVariant?.price || 0);
    return total + price * item.quantity;
  }, 0);

  const startCheckout = async () => {
    if (!customerEmail || !shippingAddress) {
      return alert("Please fill out shipping details!");
    }

    if (cartItems.length === 0) {
      return alert("Cart is empty!");
    }

    const checkoutItems = cartItems.map(item => ({
      id: item.id,
      quantity: item.quantity,
      selectedVariantId: item.selectedVariant?.id,
    }));

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/checkout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: checkoutItems,
          customer_email: customerEmail,
          shipping_address: shippingAddress,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setClientSecret(data.clientSecret);
      } else {
        alert("Checkout failed: " + (data.error || "Unknown error"));
      }
    } catch (error) {
      console.error("Checkout initiation failed", error);
      alert("Network error. Please try again.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-orange-50">
          <h2 className="text-2xl font-bold text-gray-800">Your Cart</h2>
          <button
            onClick={onClose}
            className="text-gray-500 font-bold hover:text-orange-500 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Form Inputs & Items */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!clientSecret && (
            <div className="space-y-3">
              <h3 className="font-bold text-gray-700">Shipping Details</h3>

              <input
                type="email"
                placeholder="Email Address"
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                className="w-full p-3 border rounded-xl focus:outline-orange-400"
              />

              <input
                type="text"
                placeholder="Full Delivery Address"
                value={shippingAddress}
                onChange={(e) => setShippingAddress(e.target.value)}
                className="w-full p-3 border rounded-xl focus:outline-orange-400"
              />
            </div>
          )}

          {/* Review Items */}
          <div className="border-t pt-4 space-y-4">
            <h3 className="font-bold text-gray-700">Review Items</h3>

            {cartItems.map((item) => (
              <div
                key={item.cartItemId}
                className="flex justify-between text-sm"
              >
                <span className="text-gray-600 line-clamp-1 pr-4">
                  {item.title}
                  <br />
                  <span className="text-xs text-orange-500 font-semibold">
                    {item.selectedVariant?.name}
                  </span>{' '}
                  (x{item.quantity})
                </span>

                <span className="font-bold text-gray-800">
                  $
                  {(
                    parseFloat(item.selectedVariant?.price || 0) *
                    item.quantity
                  ).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 space-y-4">
          <div className="flex justify-between font-bold text-xl text-gray-800">
            <span>Total:</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>

          {!clientSecret ? (
            <button
              onClick={startCheckout}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold py-4 rounded-xl text-lg shadow-lg transition-colors"
            >
              Proceed to Payment
            </button>
          ) : (
            <Elements stripe={stripePromise}>
              <CheckoutForm
                clientSecret={clientSecret}
                onPaymentSuccess={() => {
                  alert("🎉 Payment successful! Your pet products are on the way!");
                  localStorage.removeItem('happy-pet-cart');
                  window.location.reload();
                }}
              />
            </Elements>
          )}
        </div>
      </div>
    </div>
  );
};

export default CartSidebar;