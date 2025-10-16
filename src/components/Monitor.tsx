import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { fetchBitcoinPrice, fetchBitcoinTransactions } from '../lib/btc';
import type { Transaction } from '../types';
import { debounce } from '../utils';

const TransactionItem = memo(({ tx, isNew }: { tx: Transaction; isNew: boolean }) => (
  <div className={`p-2 sm:p-3 flex justify-between items-start bg-white ${isNew ? 'tx-new' : ''}`}>
    <div className="flex-1 min-w-0">
      <p className="font-inter font-slashed-zero text-gwey text-[12px] block truncate">Hash{' '}<a href={`https://blockchain.info/tx/${tx.fullHash}`} target="_blank" rel="noopener noreferrer" className="text-ongy hover:underline" onClick={e => e.stopPropagation()}>{tx.shortHash}</a></p>
      <p className="font-inter font-slashed-zero text-gwey text-[12px] mt-0.5">{tx.time}</p>
    </div>
    <div className="text-right ml-3 flex-shrink-0">
      <p className="font-inter font-slashed-zero text-blig text-[14px]">{tx.value}</p>
      <p className="font-inter font-slashed-zero text-gwey text-[12px] mt-0.5">${tx.valueUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
    </div>
  </div>
), (prev, next) => prev.tx.fullHash === next.tx.fullHash && prev.isNew === next.isNew);

TransactionItem.displayName = 'TransactionItem';

const Monitor = () => {
  const [loading, setLoading] = useState(true);
  const [price, setPrice] = useState(0);
  const [displayed, setDisplayed] = useState<Transaction[]>([]);
  const [txHashes, setTxHashes] = useState<Set<string>>(new Set());
  const [paused, setPaused] = useState(false);
  const [mobile, setMobile] = useState(window.innerWidth < 640);
  const [queueVersion, setQueueVersion] = useState(0);
  const cache = useRef<Set<string>>(new Set());
  const queue = useRef<Transaction[]>([]);
  const process = useRef(false);
  const state = useRef(paused);

  useEffect(() => {
    state.current = paused;
  }, [paused]);

  useEffect(() => {
    const re = debounce(() => setMobile(window.innerWidth < 640), 150);
    window.addEventListener('resize', re);
    return () => window.removeEventListener('resize', re);
  }, []);

  const toggle = useCallback(() => setPaused(p => !p), []);

  useEffect(() => {
    let active = true;
    const loadPrice = async () => {
      try {
        const p: number = await fetchBitcoinPrice();
        if (active) {
          setPrice(p);
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to fetch price:', error);
        setLoading(false);
      }
    };
    loadPrice();
    const interval = setInterval(loadPrice, 30000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const sleep = (ms: number) =>
    new Promise<void>(resolve => {
      const start: number = Date.now();
      const tick = () => {
        if (state.current || Date.now() - start >= ms) {
          resolve();
        } else {
          setTimeout(tick, 50);
        }
      };
      tick();
    });

  useEffect(() => {
    const processQueue = async () => {
      if (state.current || process.current || queue.current.length === 0) return;
      process.current = true;
      const limit = mobile ? 10 : 11;
      while (queue.current.length > 0 && !state.current) {
        const next: Transaction | undefined = queue.current.shift();
        if (!next) break;
        setDisplayed(prev => [next, ...prev].slice(0, limit));
        setTxHashes(prev => new Set(prev).add(next.fullHash));
        await sleep(1500);
      }
      process.current = false;
      if (!state.current && queue.current.length > 0) setTimeout(processQueue, 0);
    };
    processQueue();
  }, [paused, mobile, queueVersion]);

  useEffect(() => {
    if (txHashes.size === 0) return;
    const t = setTimeout(() => setTxHashes(new Set()), 300);
    return () => clearTimeout(t);
  }, [txHashes]);

  useEffect(() => {
    if (price <= 0 || paused) return;
    let active: boolean = true;
    const loadTransactions = async () => {
      if (!active) return;
      try {
        const txs: Transaction[] = await fetchBitcoinTransactions(price);
        if (txs && txs.length > 0) {
          const newTxs: Transaction[] = txs.filter(tx => !cache.current.has(tx.fullHash));
          if (newTxs.length > 0) {
            queue.current.push(...newTxs);
            setQueueVersion(v => v + 1);
          }
          cache.current = new Set(txs.map(tx => tx.fullHash));
        }
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
      }
    };
    loadTransactions();
    const interval = setInterval(loadTransactions, 2000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [price, paused]);

  return (
    <div className="min-h-screen bg-gray-50 p-2 sm:p-3 pb-20 sm:pb-3 flex flex-col text-[12px]">
      <div className="max-w-5xl mx-auto w-full flex flex-col flex-1 min-h-0">
        <div className="text-center mb-2 flex-shrink-0">
          <h1 className="font-inter font-semibold text-blig text-[14px] mb-0.5">Unconfirmed BTC Transactions</h1>
          <p className="font-inter text-blig text-[12px]">Current Bitcoin Price: <span className="font-inter font-slashed-zero">${price.toLocaleString()}</span></p>
        </div>
        {loading ? (
          <div className="flex items-center justify-center flex-1">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 sm:h-10 sm:w-10 border-b-2 border-gray-900 mx-auto mb-3"></div>
              <p className="font-inter text-blig text-[12px]">Loading data...</p>
            </div>
          </div>
        ) : (
          <div onClick={toggle} className="divide-y divide-gray-200 cursor-pointer">{displayed.map(tx => (<TransactionItem key={tx.fullHash} tx={tx} isNew={txHashes.has(tx.fullHash)} />))}</div>
        )}
        <div className="text-center mt-4 flex-shrink-0">
          <div className="flex items-center justify-center gap-4">
            <a href="https://github.com/bd53" target="_blank" rel="noopener noreferrer" className="font-inter text-blig text-[12px] hover:underline transition-colors">GitHub</a>
            <span className="text-blig">•</span>
            <a href="https://twitter.com/death_enclaimed" target="_blank" rel="noopener noreferrer" className="font-inter text-blig text-[12px] hover:underline transition-colors">Twitter</a>
          </div>
          <p className="font-inter text-blig text-[12px] mt-2">bd53 © 2025</p>
        </div>
      </div>
    </div>
  );
};

export default Monitor;
