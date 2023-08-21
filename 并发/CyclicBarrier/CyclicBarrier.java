import java.util.concurrent.BrokenBarrierException;

public class CyclicBarrier {

    public static void main(String[] args) throws InterruptedException{
        java.util.concurrent.CyclicBarrier cyclicBarrier = new java.util.concurrent.CyclicBarrier(7, () -> {
            System.out.println("****七龙珠集齐!");
        });
        for (int i = 1; i <= 7; i++) {
            final int tempInt = i;
            new Thread(() -> {
                System.out.println("集齐第 " + tempInt + "个龙珠");
                try {
                    cyclicBarrier.await();
                } catch (InterruptedException | BrokenBarrierException e) {
                    e.printStackTrace();
                }
            }).start();
        }
    }
}