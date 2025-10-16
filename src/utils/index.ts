import { Datetime } from '../types';

export const satoshisToBTC = (satoshis: number): number => satoshis / 1e8;

export const generateHash = (fullHash: string): string => `${fullHash.slice(0, 4)}-${fullHash.slice(-4)}`;

export const formatDate = (timestamp: number): string => new Date(timestamp * 1000).toLocaleString('en-US', Datetime);

export const debounce = (func: (...args: any[]) => void, wait: number) => {
  let timeout: NodeJS.Timeout;
  return (...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};