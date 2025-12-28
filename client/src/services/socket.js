import { io } from 'socket.io-client';
import store from '../store';
import { updateVesselPosition } from '../store/slices/vesselSlice';
import { updatePortCongestion } from '../store/slices/portSlice';
import { addAlert } from '../store/slices/alertSlice';

let socket = null;

export const initSocket = (token) => {
  if (socket) {
    socket.disconnect();
  }

  socket = io(process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000', {
    auth: { token },
  });

  socket.on('connect', () => {
    console.log('Socket connected');
    socket.emit('subscribe:vessels');
  });

  socket.on('disconnect', () => {
    console.log('Socket disconnected');
  });

  // Listen for vessel position updates
  socket.on('vessel:position:updated', (data) => {
    store.dispatch(updateVesselPosition(data));
  });

  // Listen for port congestion updates
  socket.on('port:congestion:updated', (data) => {
    store.dispatch(updatePortCongestion(data));
  });

  // Listen for new alerts
  socket.on('alert:created', (alert) => {
    store.dispatch(addAlert(alert));
  });

  return socket;
};

export const subscribeToPort = (portId) => {
  if (socket) {
    socket.emit('subscribe:port', portId);
  }
};

export const getSocket = () => socket;

export default { initSocket, subscribeToPort, getSocket };
