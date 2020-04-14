public class ReverseListNode{
    static class ListNode{
        int val;
        ListNode next;

        ListNode(int val, ListNode next) {
            this.val = val;
            this.next = next;
        }
    }
    // 翻转链表
    private static ListNode reverse(ListNode head){
        if (head.next == null) return head;
        ListNode last = reverse(head.next);
        head.next.next = head;
        head.next = null;
        return last;
    }
    private static ListNode successor = null;
    // 链表翻转前n个节点
    private static ListNode reverseN(ListNode head, int n){
        if (n==1) {
            successor = head.next;
            return head;
        }
        ListNode last = reverseN(head.next, n-1);
        head.next.next = head;
        head.next = successor;
        return last;
    }
    // 链表翻转从m到n
    private static ListNode reverseBetween(ListNode head, int m, int n){
        if (m==1) {
            return reverseN(head, n);
        }
        head.next = reverseBetween(head.next, m-1, n-1);
        return head;
    }


    public static void main(String[] args) {
        Scanner scan = new Scanner(System.in);
        ListNode head = null;
        int N = scan.nextInt();
        for (int i = 0; i < N; i++) {
            int temp = scan.nextInt();
            ListNode newNode = new ListNode(temp, null);
            newNode.next = head;
            head = newNode;
        }
        ListNode res = reverseBetween(head, 2, 3);
        while(res!=null){
            System.out.println(res.val);
            res = res.next;
        }
    }
}