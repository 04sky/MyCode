import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Iterator;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

public class SlidingWindow implements MyRateLimiter{
    /**
     * 每分钟限制请求数
     */
    private final long permitsPerMinute;
    /**
     * 计数器
     */
    private final TreeMap<Long, Integer> counters;

    public SlidingWindow(long permitsPerMinute) {
        this.permitsPerMinute = permitsPerMinute;
        this.counters = new TreeMap<>();
    }
    @Override
    public boolean tryAcquire() {
        long currentWindowTime = LocalDateTime.now().toEpochSecond(ZoneOffset.UTC) / 10 * 10;
        int currentWindowCount = getCurrentWindowCount(currentWindowTime);
        if (currentWindowCount >= permitsPerMinute) {
            return false;
        }
        counters.merge(currentWindowTime, 1, Integer::sum);
        return false;
    }

    private int getCurrentWindowCount(long currentWindowTime) {
        long startTime = currentWindowTime - 50;
        int result = 0;
        Iterator<Map.Entry<Long, Integer>> iterator = counters.entrySet().iterator();
        while (iterator.hasNext()) {
            Map.Entry<Long, Integer> entry = iterator.next();
            if (entry.getKey() < startTime) {
                iterator.remove();
            } else {
                result += entry.getValue();
            }
        }
        return result;
    }
}
