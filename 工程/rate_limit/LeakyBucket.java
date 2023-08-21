public class LeakyBucket implements MyRateLimiter{
    /**
     * 桶容量
     */
    private final int capacity;
    /**
     * 漏出速率
     */
    private final int permitsPerSecond;
    /**
     * 剩余水量
     */
    private long leftWater;
    /**
     * 上次注水时间
     */
    private long timestamp = System.currentTimeMillis();

    public LeakyBucket(int capacity, int permitsPerSecond) {
        this.capacity = capacity;
        this.permitsPerSecond = permitsPerSecond;
    }
    @Override
    public boolean tryAcquire() {
        long now = System.currentTimeMillis();
        long timeGap = (now - timestamp) / 1000;
        leftWater = Math.max(0, leftWater - timeGap * permitsPerSecond);
        timestamp = now;

        if (leftWater < capacity) {
            leftWater += 1;
            return true;
        }
        return false;
    }
}
