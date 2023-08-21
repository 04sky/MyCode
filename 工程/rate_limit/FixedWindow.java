public class FixedWindow implements MyRateLimiter{
    /**
     * 每秒限制请求数
     */
    private final long permitsPerSecond;

    /**
     * 上一个窗口的开始时间
     */
    public long timestamp = System.currentTimeMillis();

    /**
     * 计数器
     */
    private int counter;

    public FixedWindow(long permitsPerSecond) {
        this.permitsPerSecond = permitsPerSecond;
    }

    @Override
    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        if (now - timestamp < 1000) {
            if (counter < permitsPerSecond) {
                counter++;
                return true;
            } else {
                return false;
            }
        }
        counter = 0;
        timestamp = now;
        return true;
    }
}
